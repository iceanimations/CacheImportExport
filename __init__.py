import CacheImportExporter
reload(CacheImportExporter)
import os.path as osp
import pymel.core as pc

Window = CacheImportExporter.GUI

doCreateGeometryCache2 =r'''
// Copyright (C) 1997-2014 Autodesk, Inc., and/or its licensors.
// All rights reserved.
//
// The coded instructions, statements, computer programs, and/or related
// material (collectively the "Data") in these files contain unpublished
// information proprietary to Autodesk, Inc. ("Autodesk") and/or its licensors,
// which is protected by U.S. and Canadian federal copyright law and by
// international treaties.
//
// The Data is provided for use exclusively by You. You have the right to use,
// modify, and incorporate this Data into other products for purposes authorized 
// by the Autodesk software license agreement, without fee.
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND. AUTODESK
// DOES NOT MAKE AND HEREBY DISCLAIMS ANY EXPRESS OR IMPLIED WARRANTIES
// INCLUDING, BUT NOT LIMITED TO, THE WARRANTIES OF NON-INFRINGEMENT,
// MERCHANTABILITY OR FITNESS FOR A PARTICULAR PURPOSE, OR ARISING FROM A COURSE 
// OF DEALING, USAGE, OR TRADE PRACTICE. IN NO EVENT WILL AUTODESK AND/OR ITS
// LICENSORS BE LIABLE FOR ANY LOST REVENUES, DATA, OR PROFITS, OR SPECIAL,
// DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES, EVEN IF AUTODESK AND/OR ITS
// LICENSORS HAS BEEN ADVISED OF THE POSSIBILITY OR PROBABILITY OF SUCH DAMAGES.

//
//
//  Creation Date:  2005
//
//  Description:
//      Create Geometry Disk Cache
//        
//

proc string createSwitchNode( string $object )
{
    string $switchNode;
    int $wantTweakNode = false;
    string $newNode = createHistorySwitch( $object, $wantTweakNode );
    $switchNode = `rename $newNode "cacheSwitch#"`;
    catch(`moveSetsPostCache $object`);
    setAttr ( $switchNode + ".ihi" ) 0;
    return $switchNode;
}

proc string getFileDirFlag( string $cacheFile, 
                            string $cacheDirectory )
{
    string $fileDirFlag = ("-fileName \"" + $cacheFile+"\"" );
    if ($cacheDirectory != "") {
        $fileDirFlag += (" -directory \""+$cacheDirectory+"\" ");
    }
    return $fileDirFlag;
}

proc attachOneCachePerGeometry( string $cacheFiles[], 
                                string $objsToCache[], 
                                string $cacheDirectory, 
                                string $replaceMode,
                                string $format )
//
// This method is used when the user requests one file per geometry.
// In this case there is an xml file per geometry and each geometry
// has its own separate cacheBlend and cacheFile node.
//
{
    int $ii;
    for ($ii = 0; $ii < size($cacheFiles); $ii++) {
        string $currObj = $objsToCache[$ii];
        string $fileDirFlag = getFileDirFlag( $cacheFiles[$ii], $cacheDirectory );
        $cacheFiles[$ii] = getCacheFilePath( $cacheDirectory, $cacheFiles[$ii] );
        string $objs[] = { $currObj } ;
        string $cacheBlend[] = getCacheBlend( $objs, $replaceMode );
        
        if (size($cacheBlend) > 0) {
            string $createCmd = ("cacheFile -createCacheNode " + $fileDirFlag + " -cacheFormat \"" + $format + "\"" );
            for ($obj in $objs) {
                $createCmd += (" -cnm \"" + $obj + "\"" );
            }
            string $cacheFile = `eval $createCmd`;
            string $channels[];
            doCacheConnect( $cacheBlend[0], $cacheFile, $objs, $channels);
        } else {
            string $switchNode = createSwitchNode( $currObj );
            string $switchNodes[] = { $switchNode };
            string $channels[];
            string $attrs[] = { ($switchNode+".inp[0]") };

            // re. bug #326517
            // doCacheAttach() is used in various places, most of which don't allow a plug-in format.
            // rather than change doCacheAttach(), slip the format into $fileDirFlag
            //
            $fileDirFlag += ( " -cacheFormat \"" + $format + "\" " );

            doCacheAttach( $switchNodes, $fileDirFlag, $attrs, $channels );
        }
    }
}

proc attachOneCache( string $cacheFile,
                     string $objsToCache[], 
                     string $cacheDirectory, 
                     string $replaceMode,
                     string $format )
//
// This method  is used when the user did not request one file per geometry.
// In this case, we use a single cacheFile node (and associated xml file)
// to drive the array passed into this method.
//
{
    int $ii;
    int $objCount = size($objsToCache);
    string $fileDirFlag = getFileDirFlag( $cacheFile, $cacheDirectory );
    string $cacheBlend[] = getCacheBlend( $objsToCache, $replaceMode );
    if (size($cacheBlend) > 0) {
        string $createCmd = ("cacheFile -createCacheNode " + $fileDirFlag + " -cacheFormat \"" + $format + "\"" );
        for ($obj in $objsToCache) {
            $createCmd += (" -cnm \"" + $obj + "\"" );
        }
        string $cacheFileNode = `eval $createCmd`;
        doCacheConnect($cacheBlend[0],$cacheFileNode,$objsToCache,$objsToCache);
    } else {
        string $switchNodes[];
        string $attrs[];
        for( $ii = 0; $ii < $objCount; $ii++ ) 
        {
            $switchNodes[$ii] = createSwitchNode( $objsToCache[$ii] );
            $attrs[$ii] = ($switchNodes[$ii]+".inp[0]");
        }
        
        // re. bug #326517
        // doCacheAttach() is used in various places, most of which don't allow a plug-in format.
        // rather than change doCacheAttach(), slip the format into $fileDirFlag
        //
        $fileDirFlag += ( " -cacheFormat \"" + $format + "\" " );
        
        doCacheAttach($switchNodes,$fileDirFlag,$attrs,$objsToCache);
    }
}


proc attachCacheGroups( string $cacheFiles[],
                        string $objsToCache[], 
                        string $cacheDirectory, 
                     string $replaceMode,    
                     string $format )
{
    global string $gCacheGroupSeparator;
    string $cacheGroups[] = `getObjectsByCacheGroup($objsToCache)`;
    if (size($cacheGroups) == size($objsToCache)) {
        attachOneCache( $cacheFiles[0], $objsToCache, 
                        $cacheDirectory, $replaceMode, $format );
    } else {
        int $currGroup = 0;
        int $nextGroup = getNextCacheGroup($cacheGroups,$currGroup);
        string $currObjs[];
        while ($nextGroup > $currGroup) {
            clear($currObjs);
            for ($ii = $currGroup; $ii < $nextGroup; $ii++) {
                if ($cacheGroups[$ii] != $gCacheGroupSeparator) {
                    $currObjs[size($currObjs)] = $cacheGroups[$ii];
                }
            }
            if (size($currObjs) > 0) {
                attachOneCache( $cacheFiles[0], $currObjs,
                                $cacheDirectory, $replaceMode, $format );
            }
            $currGroup = $nextGroup;
            $nextGroup = getNextCacheGroup($cacheGroups,$currGroup);
        }
    }
}

global proc string[] doCreateGeometryCache2( int $version, string $args[] )
//
// Description:
//    Create cache files on disk for the selected shape(s) according
//  to the specified flags described below.
//
// $version == 1:
//    $args[0] = time range mode:
//        time range mode = 0 : use $args[1] and $args[2] as start-end
//        time range mode = 1 : use render globals
//        time range mode = 2 : use timeline
//  $args[1] = start frame (if time range mode == 0)
//  $args[2] = end frame (if time range mode == 0)
//
// $version == 2:    
//  $args[3] = cache file distribution, either "OneFile" or "OneFilePerFrame"
//    $args[4] = 0/1, whether to refresh during caching
//  $args[5] = directory for cache files, if "", then use project data dir
//    $args[6] = 0/1, whether to create a cache per geometry
//    $args[7] = name of cache file. An empty string can be used to specify that an auto-generated name is acceptable.
//    $args[8] = 0/1, whether the specified cache name is to be used as a prefix
// $version == 3:
//  $args[9] = action to perform: "add", "replace", "merge", "mergeDelete" or "export"
//  $args[10] = force save even if it overwrites existing files
//    $args[11] = simulation rate, the rate at which the cloth simulation is forced to run
//    $args[12] = sample mulitplier, the rate at which samples are written, as a multiple of simulation rate.
//
//  $version == 4:
//    $args[13] = 0/1, whether modifications should be inherited from the cache about to be replaced. Valid
//                only when $action == "replace".
//    $args[14] = 0/1, whether to store doubles as floats
//  $version == 5: 
//    $args[15] = name of cache format
//  $version == 6: 
//    $args[16] = 0/1, whether to export in local or world space 
//
{    
    string $cacheFiles[];
    if(( $version > 6 ) || ( size($args) > 17 )) {
        error( (uiRes("m_doCreateGeometryCache.kBadArgsError")));
        return $cacheFiles;
    }

    string  $cacheDirectory        = "";
    string    $fileName            = "";
    int        $useAsPrefix        = 0;
    int        $perGeometry        = 0;
    string  $action        = "replace";
    int     $force = 0;
    int        $inherit = 0;
    int     $doubleToFloat = 0;
    string $distribution = "OneFilePerFrame";
    
    int     $rangeMode             = $args[0];
    float      $diskCacheStartTime = $args[1];
    float      $diskCacheEndTime   = $args[2];
    float    $simulationRate        = 1.0;
    int        $sampleMultiplier    = 1;
    
    float  $startTime = $diskCacheStartTime;
    float  $endTime = $diskCacheEndTime;
    string $format = "mcx";        // Maya's default internal format

    int $worldSpace = 0;

    if( $rangeMode == 1 ) {
        $startTime = `getAttr defaultRenderGlobals.startFrame`; 
        $endTime = `getAttr defaultRenderGlobals.endFrame`; 
    } else if( $rangeMode == 2 ) {
        $startTime = `playbackOptions -q -min`;
        $endTime = `playbackOptions -q -max`;
    }
    
    if ($version > 1) {
        $distribution = $args[3];
        $cacheDirectory = $args[5];
        $perGeometry = $args[6];
        $fileName = $args[7];
        $useAsPrefix = $args[8];
    }
    if ($version > 2) {
        $action = $args[9];
        $force = $args[10];        
        
        if( size($args) > 11 ) {
            $simulationRate = $args[11];
        }        
        if( size($args) > 12 ) {
            $sampleMultiplier = $args[12];
        }
        else {
            $sampleMultiplier = 1;
        }
    }
    if( $version > 3 ) {
        $inherit = $args[13];
        $doubleToFloat = $args[14];
    }            

    if( $version > 4 ) {
        $format = $args[15];
    }            

    if( $version > 5 ) {
        $worldSpace = $args[16];
    }            

    // Call doMergeCache instead since it handles gaps between
    // caches correctly.
    if( $action == "merge" || $action == "mergeDelete" ) 
    {
        
        string $mergeArgs[];
        $mergeArgs[0] = 1;
        $mergeArgs[1] = $startTime;
        $mergeArgs[2] = $endTime;
        $mergeArgs[3] = $args[3];
        $mergeArgs[4] = $cacheDirectory;
        $mergeArgs[5] = $fileName;
        $mergeArgs[6] = $useAsPrefix;
        $mergeArgs[7] = $force;
        $mergeArgs[8] = $simulationRate;
        $mergeArgs[9] = $sampleMultiplier;
        $mergeArgs[10] = $action;
        $mergeArgs[11] = "geom";
        $mergeArgs[12] = $format;
        return doMergeCache(2, $mergeArgs);
    }
    
    // If we're replacing a cache, and inheriting modifications, 
    // the new cache should have the same translation, scaling 
    // and clipping as the original. So store these values and 
    // set after cache creation.
    //
    float $startFrame[] = {};
    float $sourceStart[] = {};
    float $sourceEnd[] = {};
    float $scale[] = {};

    select -d `ls -sl -type cacheFile`;
    string $objsToCache[] = getGeometriesToCache();

    if ($action == "add" ) {
        if (getCacheCanBeReplaced($objsToCache)) {
            if ( cacheReplaceNotAdd($objsToCache)) {            
                $action = "replace";
            }
        }
    }

    if (size($objsToCache) == 0) {
        error((uiRes("m_doCreateGeometryCache.kMustSelectGeom")));
    } else     if ($action == "replace") {
        if (!getCacheCanBeReplaced($objsToCache)) {
            return $cacheFiles;
        }
        
        if( $inherit ) {
            string $obj, $cache;
            for( $obj in $objsToCache ) {
                string $existing[] = findExistingCaches($obj);
                int $index = size($startFrame);
                $startFrame[$index] = `getAttr ($existing[0]+".startFrame")`;
                $sourceStart[$index] = `getAttr ($existing[0]+".sourceStart")`;
                $sourceEnd[$index] = `getAttr ($existing[0]+".sourceEnd")`;
                $scale[$index] = `getAttr ($existing[0]+".scale")`;
            }
        }
    }

    // If the user has existing cache groups on some of the geometry,
    // then they cannot attach new caches per geometry.
    //
    string $cacheGroups[] = `getObjectsByCacheGroup($objsToCache)`;
    if (size($cacheGroups) != size($objsToCache)) {
        $perGeometry = 1;
        $args[6] = 1; // used below in generating cache file command
        //warning( (uiRes("m_doCreateGeometryCache.kIgnoringPerGeometry")) );
    }
    
    // Check if directory has caches that might be overwritten
    //
    verifyWorkspaceFileRule( "fileCache", "cache/nCache" );
    string $cacheDirectory = getCacheDirectory($cacheDirectory, "fileCache", 
                                                $objsToCache, $fileName,
                                                $useAsPrefix, $perGeometry,
                                                $action, $force, 1);

    if ($cacheDirectory == "") {
        return $cacheFiles;
    }
    else if ($cacheDirectory == "rename") {
        performCreateGeometryCache 1 $action;
        error((uiRes("m_doCreateGeometryCache.kNameAlreadyInUse")));
        return $cacheFiles;
    }    
        
    // if we're replacing, delete active caches.
    //
    if( $action == "replace" ) {
        for( $obj in $objsToCache ) {
            string $all[] = findExistingCaches($obj);
            for( $cache in $all) {
                if( `getAttr ($cache+".enable")`) {
                    deleteCacheFile(2, {"keep",$cache});
                }
            }
        }
    }

    // create the cache(s)
    //
    if ($action == "add" || $action == "replace") {
        setCacheEnable(0, 1, $objsToCache);
    }
    
    // generate the cacheFile command to write the caches
    //
    string $cacheCmd = getCacheFileCmd($version, $cacheDirectory, $args);
    int $ii = 0;
    
    //segmented cache files are employed in the case of one large cache file that
    //exceeds 2GB in size.  Since we currently cannot handle such large files, we will
    //automatically generate several caches, each less than 2GB.
    int $useSegmentedCacheFile = 0;
    int $numSegments = 0; 
    if($distribution == "OneFile" && !$perGeometry) {
        string $queryCacheSizeCmd = "cacheFile";
        for ($ii = 0; $ii < size($objsToCache); $ii++) {
            $queryCacheSizeCmd += (" -points "+$objsToCache[$ii]);
        }
        $queryCacheSizeCmd += " -q -dataSize";
        if($doubleToFloat) {
            $queryCacheSizeCmd += " -dtf";
        }
        float $dataSizePerFrame = `eval $queryCacheSizeCmd`;
        float $maxSize = 2147000000; //approximate size of max signed int.
        float $numSamples = ($endTime - $startTime + 1.0)/($simulationRate*$sampleMultiplier);
        float $dataSize = $dataSizePerFrame*$numSamples;
        if($dataSize > $maxSize) {
            $useSegmentedCacheFile = 1;
            $numSegments = floor($dataSize / $maxSize) + 1;                                    
        }
    }
    
    if(!$useSegmentedCacheFile) {        
        if( $fileName != "" ) {
            $cacheCmd += ("-fileName \"" + $fileName + "\" ");
        }
        $cacheCmd += ("-st "+$startTime+" -et "+$endTime);

        // if we're exporting vertex data only, can do it in world space too            
        if(($action == "export") && size($objsToCache) > 0 && $worldSpace > 0 ) {
                $cacheCmd += (" -worldSpace ");
        }

        for ($ii = 0; $ii < size($objsToCache); $ii++) {
            $cacheCmd += (" -points "+$objsToCache[$ii]);
        }
        $cacheFiles = `eval $cacheCmd`;
    }
    else {
        int $jj;
        float $segmentStartTime = $startTime;
        float $segmentEndTime;
        float $segmentLength = ($endTime - $startTime)/$numSegments;
        string $segmentCacheCmd ;
        string $segmentCacheName = "";
        string $segmentCacheFiles[];
        for($jj = 0; $jj< $numSegments; $jj++) {            
            $segmentCacheCmd = $cacheCmd;
            if($fileName != "") 
                $segmentCacheName = $fileName;                        
            else
                $segmentCacheName = getAutomaticCacheName();
            $segmentEndTime = $segmentStartTime + floor($segmentLength);                       
                        
            $segmentCacheName += ("Segment" + ($jj+1));
            $segmentCacheCmd += (" -fileName \"" + $segmentCacheName + "\" ");            
                          
            $segmentCacheCmd += ("-st "+$segmentStartTime+" -et "+$segmentEndTime);
        
           // if we're exporting vertex data only, can do it in world space too            
            if(($action == "export") && size($objsToCache) > 0 && $worldSpace > 0 ) {
                   $segmentCacheCmd += (" -worldSpace ");
           }

            for ($ii = 0; $ii < size($objsToCache); $ii++) {
                $segmentCacheCmd += (" -points "+$objsToCache[$ii]);
            }
            $segmentCacheFiles = `eval $segmentCacheCmd`;
            $segmentStartTime = $segmentEndTime + 1;
            
            $cacheFiles[size($cacheFiles)] = $segmentCacheFiles[0];
        }        
    }

    if ($action == "export") {
        for ($ii = 0; $ii < size($cacheFiles); $ii++) {
            $cacheFiles[$ii] = ($cacheDirectory+"/"+$cacheFiles[$ii]+".xml");
        }
        // In export mode, we do not want to attach the cache. We are done.
        //
        return $cacheFiles;
    }
    
        
    // attach the caches to the history switch
    //
    if($useSegmentedCacheFile) {
        if(size($objsToCache) == 1) {
            for($ii=0;$ii<size($cacheFiles);$ii++) {
                string $segmentCacheFile[];
                $segmentCacheFile[0] = $cacheFiles[$ii];
                attachOneCachePerGeometry(     $segmentCacheFile, $objsToCache, 
                                    $cacheDirectory, $action, $format );
            }
        }
        else {
            for($ii=0;$ii<size($cacheFiles);$ii++) {
                string $segmentCacheFile[];
                $segmentCacheFile[0] = $cacheFiles[$ii];
                attachCacheGroups( $segmentCacheFile,$objsToCache,$cacheDirectory,$action, $format );
            }            
        }
        
    }
    else if( $perGeometry || size($objsToCache) == 1) {
        attachOneCachePerGeometry(     $cacheFiles, $objsToCache, 
                                    $cacheDirectory, $action, $format );
    } else {
        if( size($cacheFiles) != 1 ) {
            error( (uiRes("m_doCreateGeometryCache.kInvalidCacheOptions")));
        }
        
        attachCacheGroups( $cacheFiles,$objsToCache,$cacheDirectory,$action, $format );        
        
    }

    // If we're replacing a cache and inheriting modifications,
    // restore the translation, scaling, clipping etc.
    if( $action == "replace" && $inherit ) 
    {
        int $i = 0;
        for( $i = 0; $i < size($objsToCache); $i++) 
        {
            string $cache[] = findExistingCaches($objsToCache[$i]);
            float $sStart = `getAttr ($cache[0]+".sourceStart")`;
            float $sEnd = `getAttr ($cache[0]+".sourceEnd")`;
            
            if( $sStart != $sourceStart[$i] &&
                $sourceStart[$i] >= $sStart &&
                $sourceStart[$i] <= $sEnd )
            {
                cacheClipTrimBefore( $cache[0], $sourceStart[$i] );
            }
            
            if( $sEnd != $sourceEnd[$i] &&
                $sourceEnd[$i] >= $sStart &&
                $sourceEnd[$i] <= $sEnd )
            {
                cacheClipTrimAfter( $cache[0], $sourceEnd[$i] );
            }
            
            setAttr ($cache[0] + ".startFrame") $startFrame[$i];
            setAttr ($cache[0] + ".scale") $scale[$i];
        }
    }
    select -r $objsToCache;
    return $cacheFiles;
}

'''

pc.Mel.eval(doCreateGeometryCache2)